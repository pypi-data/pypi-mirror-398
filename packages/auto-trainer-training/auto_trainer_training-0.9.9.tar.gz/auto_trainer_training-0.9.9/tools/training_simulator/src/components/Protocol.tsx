import {Card, Divider, Group, Select, SimpleGrid, Stack, Text, Tooltip} from "@mantine/core";
import {Dropzone} from "@mantine/dropzone";
import {IconJson, IconUpload, IconX} from "@tabler/icons-react";

import type {TrainingProtocol} from "../models/trainingProtocol.ts";
import {LoadProtocol} from "../pywebview.ts";

export const Protocol = ({protocol}: { protocol: TrainingProtocol }) => {
    return (
        <Card mih={240} withBorder>
            <Card.Section bg="blue.2">
                <Group p={4} justify="space-between">
                    <Text fw={500}>Protocol</Text>
                    {protocol ? <Tooltip label={protocol.description}><Text size="sm" c="dimmed">{protocol.name}</Text></Tooltip> : null}
                </Group>
            </Card.Section>
            {protocol ? <ProtocolContent protocol={protocol}/> : <NoProtocol/>}
        </Card>
    );
}

const ProtocolContent = ({protocol}: { protocol: TrainingProtocol }) => {
    const phases = protocol.phases.map((phase, idx) => {
        const stackProps = idx == 5 ? {bdrs: 4, bd: "1px solid #999"} : {};
        const props = idx == 5 ? {fw: 500, c: "green.6"} : {};

        return (
            <Stack gap={0} {...stackProps} p={8}>
                <Text size="sm" {...props}>{`${idx + 1}. ${phase.name}`}</Text>
                <Text size="xs" c="dimmed" lineClamp={2}>{phase.description}</Text>
            </Stack>
        )
    })
    return (
        <Stack>
            <Text size="sm" c="dimmed">{protocol.description}</Text>
            <SimpleGrid cols={3}>
                {phases}
            </SimpleGrid>
        </Stack>
    );
}

const NoProtocol = () => {
    const onFileReceived = (acceptedFiles: File[]) => {
        if (acceptedFiles && acceptedFiles.length > 0) {
            const reader = new FileReader();
            reader.onload = ((data: ProgressEvent) => {
                if (data.loaded == data.total) {
                    LoadProtocol(acceptedFiles[0].name, reader.result as string);
                }
            });
            reader.readAsText(acceptedFiles[0]);
        }
    }

    return (
        <Card.Section>
            <Stack gap={0}>
                <Group p={8} gap="sm">
                    <Text>Training protocol:</Text>
                    <Select/>
                </Group>
                <Divider orientation="horizontal"/>
                <Dropzone bd="none" w={"100%"} accept={["application/json"]} onDrop={onFileReceived}>
                    <Group justify="center" gap="xl" mih={120} style={{pointerEvents: 'none'}}>
                        <Dropzone.Accept>
                            <IconUpload size={52} color="var(--mantine-color-blue-6)" stroke={1.5}/>
                        </Dropzone.Accept>
                        <Dropzone.Reject>
                            <IconX size={52} color="var(--mantine-color-red-6)" stroke={1.5}/>
                        </Dropzone.Reject>
                        <Dropzone.Idle>
                            <IconJson size={52} color="var(--mantine-color-dimmed)" stroke={1.5}/>
                        </Dropzone.Idle>
                        <div>
                            <Text size="xl" inline>
                                Drag a protocol json file here or click to select a custom protocol
                            </Text>
                            <Text size="sm" c="dimmed" inline mt={7}>
                                Standard training protocols are listed in the dropdown above
                            </Text>
                        </div>
                    </Group>
                </Dropzone>
            </Stack>
        </Card.Section>
    );
}